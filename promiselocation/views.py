from django.shortcuts import render, redirect
from mypage.models import CreateCommunity
from community.models import CommunityMember
from account.models import User
from promise.models import PromiseResult
from django.http import HttpResponse
import requests
from dotenv import load_dotenv
import os
import time
from django.contrib import messages
import numpy as np
import json
# .env 파일에서 환경변수 로드
load_dotenv()

def get_nearby_places_all_types(lat, lng, api_key, radius=500):
    """
    지정된 다섯 가지 타입(cafe, convenience_store 등)의 장소를 가져온다.
    결과가 없어도 함수는 빈 리스트를 반환한다.
    """
    place_types = ['cafe', 'convenience_store', 'subway_station', 'restaurant']
    all_places = []

    for place_type in place_types:
        try:
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "type": place_type,
                "key": api_key,
            }

            response = requests.get(url, params=params)
            data = response.json()

            if data.get("status") == "OK":
                for place in data["results"]:
                    all_places.append({
                        'name': place['name'],
                        'address': place.get('vicinity'),
                        'rating': place.get('rating'),
                        'type': place_type,
                        'location': place['geometry']['location']
                    })
            elif data.get("status") == "ZERO_RESULTS":
                print(f"[{place_type}] 반경 내 결과 없음.")
            else:
                print(f"Places API Error ({place_type}):", data.get("error_message", data.get("status", "알 수 없는 오류")))

        except Exception as e:
            print(f"[{place_type}] 요청 중 오류 발생:", e)

    print("총 검색된 장소 수:", len(all_places))
    return all_places


def find_optimal_midpoint(points, api_key, standard_time_gap=15, sleep_seconds=10):
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


from django.http import JsonResponse
from django.urls import reverse

def location(request, community_id, promise_id):
    # POST나 GET 관계없이 허용 → 버튼 클릭은 GET 요청
    community = CreateCommunity.objects.get(id=community_id)
    community_members = CommunityMember.objects.filter(community_name=community.community_name)
    member_usernames = community_members.values_list('member', flat=True)
    members = User.objects.filter(username__in=member_usernames)

    # 멤버 좌표 수집
    members_with_coords = []
    for member in members:
        members_with_coords.append({
            'username': member.username,
            'address': member.address,
            'longitude': member.longitude,
            'latitude': member.latitude,
        })

    points = {
        m['username']: np.array([m['latitude'], m['longitude']])
        for m in members_with_coords
    }

    api_key = os.getenv('ODsay_APIKEY')
    Google_api_key = os.getenv('Google_API')

    # ✅ 모두 투표 완료 여부 확인
    promise_result = PromiseResult.objects.filter(promise_id=promise_id).first()
    if not promise_result:
        messages.warning(request, '투표가 종료된 후 눌러주세요!')
        return redirect('community:promise:promise_result', community_id=community_id, promise_id=promise_id)

    # ✅ 중간지점 계산
    mid_point, default_time = find_optimal_midpoint(points, api_key)

    # ✅ 장소 데이터 가져오기
    places = get_nearby_places_all_types(
        lat=mid_point[0],
        lng=mid_point[1],
        api_key=Google_api_key,
        radius=500
    )

    # 중간지점/places 저장
    promise_result.center_latitude = float(mid_point[0])
    promise_result.center_longitude = float(mid_point[1])
    promise_result.places_json = json.dumps(places, ensure_ascii=False)
    promise_result.save()

    # ✅ JS에서 리디렉션 처리하게 URL만 반환
    return JsonResponse({
        "success": True,
        "redirect_url": reverse("community:promise:promise_result", args=[community_id, promise_id])
    })