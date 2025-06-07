function openModal(index) {
  const modal = document.getElementById(`modal-${index}`);
  const content = modal.querySelector(".modal-content");

  modal.style.display = "block";
  document.body.classList.add("modal-open");

  // 히스토리에 모달 상태 추가
  history.pushState({ modalOpen: true, index }, '', '');

  // 애니메이션 강제 재실행
  content.classList.remove("slide-top");
  void content.offsetWidth;
  content.classList.add("slide-top");
}
  
function closeModal(index) {

  const modal = document.getElementById(`modal-${index}`);
  
  // 먼저 스크롤 초기화
  modal.scrollTop = 0;

  // 히스토리에 모달 상태 추가
  history.pushState({ modalOpen: false, index }, '', '');

  document.getElementById(`modal-${index}`).style.display = "none";
  document.body.classList.remove("modal-open");
  resetCards(index);  // 이 줄 추가!
}

window.addEventListener("popstate", (event) => {
  const state = event.state;
  if (state && state.modalOpen) {
    closeModal(state.index);
  }
});

function loadMoreCards(modalIndex) {
  const modal = document.getElementById(`modal-${modalIndex}`);
  const cards = modal.querySelectorAll(".modal-news-card");
  const button = modal.querySelector("#load-more-news");

  // 현재 보이는 카드 수 계산
  let visibleCount = 0;
  cards.forEach(card => {
    if (card.style.display == "block") visibleCount++;
  });

  // 다음 8개만 표시
  for (let i = visibleCount; i < visibleCount + 8 && i < cards.length; i++) {
    cards[i].style.display = "block";
  }

  // 카드 전부 노출되면 버튼 숨기기
  if (visibleCount + 8 >= cards.length && button) {
    button.style.display = "none";
  }
}

function resetCards(modalIndex) {
  const modal = document.getElementById(`modal-${modalIndex}`);
  const cards = modal.querySelectorAll(".modal-news-card");
  let visibleCount = 8;

  cards.forEach((card, index) => {
    card.style.display = index < visibleCount ? "block" : "none";
  });

  const btn = modal.querySelector("#load-more-news");
  if (btn) btn.style.display = "block";
}

document.addEventListener("DOMContentLoaded", () => {
  const allNewsContainers = document.querySelectorAll(".modal-news");
  allNewsContainers.forEach(container => {
    const cards = container.querySelectorAll(".modal-news-card");
    for (let i = 0; i < 8 && i < cards.length; i++) {
      cards[i].style.display = "block";
    }
  });
});


const slideIndexMap = new Map();
slideIndexMap.set('grid-1', 0);
slideIndexMap.set('grid-2', 0);
slideIndexMap.set('grid-3', 0);

function updateSlide_countries(slideIndex, nextIndex) {
  const slides = document.querySelectorAll(`.slide-countries-grid-${slideIndex}`);
  slides.forEach((slide, i) => {
    slide.style.transform = `translateX(-${nextIndex * 100}%)`;
    slide.style.transition = 'transform 0.5s ease';
  });
}

function nextSlide_countries(slideIndex) {
  const slides = document.querySelectorAll(`.slide-countries-grid-${slideIndex}`);
  const currentIndex = slideIndexMap.get(`grid-${slideIndex}`);
  const nextIndex = (currentIndex + 1) % slides.length;
  slideIndexMap.set(`grid-${slideIndex}`, nextIndex);
  updateSlide_countries(slideIndex, nextIndex);
}

function prevSlide_countries(slideIndex) {
  const slides = document.querySelectorAll(`.slide-countries-grid-${slideIndex}`);
  const currentIndex = slideIndexMap.get(`grid-${slideIndex}`);
  const nextIndex = (currentIndex - 1) % slides.length;
  slideIndexMap.set(`grid-${slideIndex}`, nextIndex);
  updateSlide_countries(slideIndex, nextIndex);
}


function updateSlide_companies(slideIndex, nextIndex) {
  const slides = document.querySelectorAll(`.slide-companies-grid-${slideIndex}`);
  slides.forEach((slide, i) => {
    slide.style.transform = `translateX(-${nextIndex * 100}%)`;
    slide.style.transition = 'transform 0.5s ease';
  });
}

function nextSlide_companies(slideIndex) {
  const slides = document.querySelectorAll(`.slide-companies-grid-${slideIndex}`);
  const currentIndex = slideIndexMap.get(`grid-${slideIndex}`);
  const nextIndex = (currentIndex + 1) % slides.length;
  slideIndexMap.set(`grid-${slideIndex}`, nextIndex);
  updateSlide_companies(slideIndex, nextIndex);
}

function prevSlide_companies(slideIndex) {
  const slides = document.querySelectorAll(`.slide-companies-grid-${slideIndex}`);
  const currentIndex = slideIndexMap.get(`grid-${slideIndex}`);
  const nextIndex = (currentIndex - 1) % slides.length;
  slideIndexMap.set(`grid-${slideIndex}`, nextIndex);
  updateSlide_companies(slideIndex, nextIndex);
}