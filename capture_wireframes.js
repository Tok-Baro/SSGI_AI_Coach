const puppeteer = require("puppeteer");
const path = require("path");

(async () => {
  const browser = await puppeteer.launch({ headless: "new" });
  const page = await browser.newPage();

  const filePath = path.resolve(__dirname, "wireframe.html");
  await page.goto(`file://${filePath}`, { waitUntil: "networkidle0", timeout: 30000 });

  // 1. 전체 와이어프레임 한장 캡처
  await page.setViewport({ width: 1800, height: 10000 });
  await page.goto(`file://${filePath}`, { waitUntil: "networkidle0" });
  const fullHeight = await page.evaluate(() => document.body.scrollHeight);
  await page.setViewport({ width: 1800, height: fullHeight });
  await page.screenshot({
    path: path.resolve(__dirname, "wireframes/00_전체_와이어프레임.png"),
    fullPage: true,
  });
  console.log("✓ 전체 와이어프레임 캡처 완료");

  // 2. 각 화면별 개별 캡처 (phone-frame 요소들)
  const screens = await page.$$(".phone-frame");
  const labels = await page.$$(".screen-sublabel");

  const screenNames = [
    "01_랜딩_로그인",
    "02_카카오_인증처리",
    "03_카카오_인증에러",
    "04_온보딩_사업자번호",
    "05_온보딩_상호명검색",
    "06_온보딩_확인",
    "07_온보딩_완료",
    "08_대시보드_홈",
    "09_대시보드_음성질의",
    "10_지원사업_매칭",
    "11_사업계획서_모달",
    "12_QR쿠폰_목록",
    "13_쿠폰만들기_모달",
    "14_글로벌에러",
  ];

  for (let i = 0; i < screens.length; i++) {
    const name = screenNames[i] || `screen_${i + 1}`;
    try {
      await screens[i].screenshot({
        path: path.resolve(__dirname, `wireframes/${name}.png`),
      });
      console.log(`✓ ${name} 캡처 완료`);
    } catch (e) {
      console.log(`✗ ${name} 캡처 실패: ${e.message}`);
    }
  }

  await browser.close();
  console.log("\n모든 캡처 완료! wireframes/ 폴더를 확인하세요.");
})();
