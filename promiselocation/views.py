from django.shortcuts import render, redirect
from mypage.models import CreateCommunity
from community.models import CommunityMember
from account.models import User
from promise.models import PromiseResult

import requests
from dotenv import load_dotenv
import os
import time
# .env 파일에서 환경변수 로드
load_dotenv()

import numpy as np
import requests
import time

def find_optimal_midpoint(points, api_key, standard_time_gap=20, sleep_seconds=10):
    """
    사용자 좌표(points)와 ODsay API를 사용해 
    최적의 중간지점을 찾아 반환하는 함수.
    
    :param points: {'A': np.array([lat, lon]), 'B': np.array([lat, lon]), ...}
    :param api_key: ODsay API 키
    :param standard_time_gap: 허용할 최대 소요 시간 차이 (분)
    :param sleep_seconds: API 과도 호출 방지를 위한 대기 시간 (초)
    :return: (mid_point, defult_time)
             mid_point → np.array([lat, lon])
             defult_time → {'A': 30, 'B': 40, ...}
    """
    url = 'https://api.odsay.com/v1/api/searchPubTransPathT'
    mid_point = np.sum(list(points.values()), axis=0) / len(points)
    unit_vecs = {}
    vecs_weight = {}
    defult_time = {key: 0 for key in points.keys()}
    trial = 1

    while True:
        end_lat, end_lon = mid_point

        for name, value in points.items():
            start_lat, start_lon = points[name]
            params = {
                'SX': float(start_lon),
                'SY': float(start_lat),
                'EX': float(end_lon),
                'EY': float(end_lat),
                'apiKey': api_key
            }

            response = requests.get(url, params=params)
            data = response.json()

            # 최단 시간 찾기
            short_time = data['result']['path'][0]['info']['totalTime']
            for i in range(len(data['result']['path'])):
                time_cost = data['result']['path'][i]['info']['totalTime']
                if time_cost < short_time:
                    short_time = time_cost

            defult_time[name] = short_time

        time_gap = max(defult_time.values()) - min(defult_time.values())
        print(f'[{trial}회차] 소요 시간 차이: {time_gap}분')

        if time_gap <= standard_time_gap:
            print(f"최종 중간지점: {mid_point}")
            return mid_point, defult_time

        # 소요 시간 차이가 크면 중간지점 보정
        for name, point in points.items():
            vec = point - mid_point
            norm = np.linalg.norm(vec)
            unit_vec = vec / norm if norm != 0 else np.array([0, 0])
            unit_vecs[name] = unit_vec

        for name, vec in unit_vecs.items():
            vecs_weight[name] = vec * defult_time[name]

        avg_vec = sum(vecs_weight.values()) / len(points)
        mid_point += (avg_vec * 0.01)

        trial += 1
        time.sleep(sleep_seconds)


def location(request, community_id, promise_id):
    # 1️⃣ 멤버 정보 가져오기
    community = CreateCommunity.objects.get(id=community_id)
    community_members = CommunityMember.objects.filter(community_name=community.community_name)
    member_usernames = community_members.values_list('member', flat=True)
    members = User.objects.filter(username__in=member_usernames)

    # 2️⃣ members_with_coords 만들기
    members_with_coords = []
    for member in members:
        members_with_coords.append({
            'username': member.username,
            'address': member.address,
            'longitude': member.longitude,
            'latitude': member.latitude,
        })

    # 3️⃣ points 딕셔너리 생성
    points = {
        m['username']: np.array([m['latitude'], m['longitude']])
        for m in members_with_coords
    }

    # 4️⃣ API 키 가져오기 (dotenv에서)
    api_key = os.getenv('ODsay_APIKEY')

    # 5️⃣ 알고리즘 함수 호출 → 중간지점 계산
    mid_point, defult_time = find_optimal_midpoint(points, api_key)

    # 6️⃣ PromiseResult 모델 업데이트
    promise_result = PromiseResult.objects.get(promise_id=promise_id)
    promise_result.center_latitude = float(mid_point[0])
    promise_result.center_longitude = float(mid_point[1])
    promise_result.save()

    # 7️⃣ redirect → context 대신 promise_id만 넘기기
    return redirect('community:promise:promise_result', community_id=community_id, promise_id=promise_id)