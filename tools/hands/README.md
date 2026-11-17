# 손가락 자리 손 그림

- left.webp: 이미지 생성 도구(Carat, GPT Image 2.6)로 만든 아이 왼손(위에서 본 손등, 투명 배경)
- slice.py: 손바닥(엄지 포함)과 손가락 4개로 자르고 오른손은 좌우로 뒤집어 hands.json을 만듦. src.html의 FG_HANDS에 넣어 씀

    python3 tools/hands/slice.py tools/hands/left.webp /tmp/hands.json
