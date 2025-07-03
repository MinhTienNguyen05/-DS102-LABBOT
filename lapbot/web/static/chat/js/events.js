import { postUserMessage, deleteAllMessages, postDataToPredictPrice } from "./apis";
import { formatCurrency } from '../../global/js/utils'

// import Swiper bundle with all modules installed
import Swiper from 'swiper/bundle';
// import styles bundle
import 'swiper/css/bundle';

function autoResize(element) {
    element.style.height = 'auto'; // Reset lại height (không giữ height cũ khi xóa text)
    const maxHeight = 240; // Max height
    element.style.height = Math.min(element.scrollHeight, maxHeight) + 'px';
}

function updateContentHeight() {
    const header = document.getElementById('header')
    const content = document.getElementById('content')
    
    const headerHeight = header.offsetHeight;
    const contentHeight = window.innerHeight - headerHeight;
    console.log(headerHeight, contentHeight)

    content.style.height = `${contentHeight}px`;
}

function setObserveChatResponesHeight() {
    const chatContainerInput = document.getElementById('chat-container_input');
    const chatContainerResponse = document.getElementById('chat-container_response');

    const content = document.getElementById('content')
    const contentHeight = content.offsetHeight

    const observer = new ResizeObserver(entries => {
        for (let entry of entries) {
            const chatContainerInputHeight = entry.contentRect.height;
            chatContainerResponse.style.height = `${contentHeight - chatContainerInputHeight}px`;
        }
    });

    // Quan sát thay đổi kích thước topBar
    observer.observe(chatContainerInput);
}

function scrollToEndElement() {
    const elementScroll = document.querySelector('.scrollToEnd')

    if (elementScroll) {
        elementScroll.scrollIntoView({
            behavior: 'smooth',
            block: 'end'
        })
    }
}

// Tạo swiper
function initSwiper() {
    const mySwiper = new Swiper('.multiple-slide-carousel', {
        loop: false,
        slidesPerView: 3,
        spaceBetween: 20,
        padding: 0,
        navigation: {
            nextEl: '.multiple-slide-carousel .slider-button-next',
            prevEl: '.multiple-slide-carousel .slider-button-prev',
        },
        breakpoints: {
            0: {
                slidesPerView: 3,
                spaceBetween: 20,
            },
        },
        on: {
            init: function () { // Buộc xài function() chứ k đc arrow func vì this ở đây là Swiper instance
                updateNavButtons(this); // cập nhật trạng thái nút ngay khi khởi tạo
            },
            slideChange: function () {
                updateNavButtons(this); // cập nhật mỗi khi chuyển slide
            },
        },
    });
}


// Hàm cập nhật trạng thái enable/disable của nút prev/next của swiper
function updateNavButtons(swiperInstance) {
    const prevButton = document.querySelector('.slider-button-prev');
    const nextButton = document.querySelector('.slider-button-next');

    if (swiperInstance.isBeginning) {
        prevButton.style.display = 'none';
    } else {
        prevButton.style.display = 'block';
    }

    // Disable nút next nếu đang ở slide cuối
    if (swiperInstance.isEnd) {
        nextButton.style.display = 'none';
    } else {
        nextButton.style.display = 'block';
    }
}

function changeStyleCurrency(element = document) {
    const allPrice = element.querySelectorAll('.price_vnd')

    allPrice.forEach(element => {
        element.innerHTML = formatCurrency(parseInt(element.innerHTML))
    });
}

async function appendMessageBlock(message, role='user') {
    const parentContainer = document.getElementById('chat-container_response--body')

    const data = await postUserMessage(message, role)
    const container = document.createElement('div');

    container.innerHTML = data.html;

    parentContainer.appendChild(container);

    if (role == 'ai') {
        initSwiper()
        changeStyleCurrency(container)
    }
}

// Run 1 lần duy nhất
window.addEventListener('DOMContentLoaded', () => {
    // Resize chat input
        const textarea = document.getElementById('chat-container_input--bar')
        if (textarea) {
            // Add event mỗi lần input -> call autoResize()
            textarea.addEventListener('input', () => autoResize(textarea))
        }

    // Set height cho content
        // Gọi ngay lập tức
        updateContentHeight();
        // Gọi lại mỗi khi scroll hoặc resize
        window.addEventListener('resize', updateContentHeight);
    
    // Check input tăng row -> đẩy content lên để không bị mất nội dung
        setObserveChatResponesHeight()

    // Scroll chat đến cuối
        scrollToEndElement()
    
    // Load swiper nếu đang ở session
        initSwiper()
    
    // Load price currency lần đầu
        changeStyleCurrency()

    // Tạo block user message khi button form click
        const sendMessageButton = document.getElementById('chat-container_input--button')
        sendMessageButton.addEventListener('click', () => {
            let currentValue = textarea.value
            
            // Xử lí block user
            appendMessageBlock(currentValue, 'user')
            textarea.value = ''
            // Xử lí block AI
            appendMessageBlock(currentValue, 'ai')
        }) 
    
    // Dynamic DOM (sử dụng Event Delegation)
        document.addEventListener('click', async (event) => {

            // Nếu click để confirm delete -> Call API delete
            const confirmResetChatButton = event.target.closest('#reset-chat_confirm');

            if (confirmResetChatButton) {
                console.log('Click reset chat confirm !! (via delegation)');
                // Xóa session data BE
                await deleteAllMessages()
                // Xóa UI hiện bên FE
                const parentContainer = document.getElementById('chat-container_response--body')
                parentContainer.innerHTML = ''
            }
        })
})

// Khi dùng Vite (hoặc bất kỳ bundler hiện đại nào như Webpack, ESBuild...), các hàm trong module ES6 
// mặc định không được gán vào global scope (window)
window.postDataToPredictPrice = postDataToPredictPrice