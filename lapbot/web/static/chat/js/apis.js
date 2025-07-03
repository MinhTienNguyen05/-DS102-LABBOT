async function customFetch(url, options = {}) {
  // Mặc định method là GET
    const {
        method = 'GET',
        headers = {},
        body = null,
    } = options;

    try {
        const response = await fetch(url, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null,
        });

        if (!response.ok) {
            // Nếu status code không trong khoảng 200-299, throw lỗi
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Giả sử response là JSON
        const data = await response.json();
        return data;

    } catch (error) {
        console.error('Fetch error:', error);
        throw error;  // đẩy lỗi lên phía gọi hàm xử lý
    }
}

async function postUserMessage(message, role='user') {
    let endpoint = '/chat/user_message_html/'
    if (role == 'ai') {
        endpoint = '/chat/ai_message_html/'
    }

    try {
        const data = await customFetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: {
                data: {
                    user_message: message
                }
            },
        });

        console.log(data)
        console.log(data)
        return data

    } catch (error) {
        console.error('Error loading chat block:', error);
    }
}

async function postDataToPredictPrice() {
    let endpoint = '/chat/predict_price/'
    try {
        const data = await customFetch(endpoint, {
            method: 'POST',
            // headers: {
            //     'Content-Type': 'application/json',
            // },
        })

        console.log(data)
    } catch (error) {
        console.error('Error loading chat block:', error);
    }
}

async function deleteAllMessages() {
    let endpoint = '/chat/delete_all_message/'

    try {
        const data = await customFetch(endpoint, {
            method: 'POST',
            // headers: {
            //     'Content-Type': 'application/json',
            //     'X-CSRFToken': getCSRFToken(), // nếu Django đang bảo vệ CSRF
            // },
            // credentials: 'include', // rất quan trọng nếu bạn dùng session login
        });

        console.log('Response:', data);
        return data
        
    } catch (error) {
        console.error('Error deleting messages:', error);
    }
}


export { postUserMessage, deleteAllMessages, postDataToPredictPrice }