# 손가락 자리 손 그림

- left.webp: 이미지 생성 도구(Carat, GPT Image 2.6)로 만든 아이 왼손(위에서 본 손등, 투명 배경)
- slice.py: 손은 자르지 않고 그대로 쓰고, 손가락마다 손등 쪽으로 옅어지는 강조용 조각을 만듦. 오른손은 좌우로 뒤집음. 결과 hands.json을 src.html의 FG_HANDS에 넣어 씀

    python3 tools/hands/slice.py tools/hands/left.webp /tmp/hands.json
