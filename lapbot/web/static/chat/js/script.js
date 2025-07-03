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

function setActionForm() {
    const chatForm = document.getElementById('chat-container_input');
    const formActionHiddenInput = document.getElementById('chat-container_hidden-input');
    const sendMessageButton = document.getElementById('chat-container_input--button');

    if (sendMessageButton) {
        sendMessageButton.addEventListener('click', () => {
            formActionHiddenInput.value = 'send_message';
            chatForm.submit();
        });
    }

    document.addEventListener('click', (event) => {
        console.log('Document clicked!')
        const confirmResetChatButton = event.target.closest('#reset-chat_confirm');

        if (confirmResetChatButton) {
            console.log('Click reset chat confirm !! (via delegation)');
            formActionHiddenInput.value = 'reset_chat';
            chatForm.submit();
        }
    })
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

    // Chỉnh value action cho submit form
        setActionForm()

    // Scroll chat đến cuối
        scrollToEndElement()
})