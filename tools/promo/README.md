# 홍보영상 (30초, HyperFrames)

다시 만들 때 순서:
1. `python3 build.py` 후 `index.html`을 `page.html`로 복사 (capture.js가 `../page.html`을 열어요)
2. `npx hyperframes@0.9.26 init island --example blank --non-interactive --skip-skills` 로 프로젝트를 만들고, 게임 그림(assets/*.json에서 꺼낸 PNG)·원정 그림(assets/codex_exp_*.jpg)·글꼴(Google Fonts의 Bagel Fat One, IBM Plex Sans KR, Nanum Gothic Coding, OFL)을 `island/assets/`에 둠
3. `node capture.js` : 화면 UI를 숨긴 섬, 마을 낮·밤, 밤 침공 장면을 1920×1080 @2x로 찍고 건물 자리 좌표(plan.json)와 배 위치(raid.json)를 기록
4. `python3 gen.py` : 같은 시간표로 `island/index.html`(GSAP 타임라인)과 `island/assets/audio.wav`(오르골 반주, 타자·건물·침공 효과음 직접 합성)를 만듦
5. `npx hyperframes@0.9.26 render -q looks -w 4 -o promo_silent.mp4` 후
   `ffmpeg -i promo_silent.mp4 -i island/assets/audio.wav -af loudnorm=I=-16:TP=-1.5:LRA=11 -c:v copy -c:a aac -b:a 192k -shortest out.mp4`

경로는 작업했던 세션의 임시 폴더 기준이라 다시 쓸 때 `gen.py`의 `D`를 고쳐요.
