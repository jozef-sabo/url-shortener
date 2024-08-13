const destinationInput = document.getElementById('destination');
const errorMessage = document.getElementById('error-message');

const submitButton = document.querySelector('button[type="submit"]');
const urlForm = document.getElementById('url-form');
const notification = document.getElementById('notification');

// Regex for validating URL including port numbers
const urlPattern = /^(https?:\/\/)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(:\d{1,5})?(\/.*)?$/;

const defaultErrorText = "Invalid URL format. Please include http(s) and valid characters.";

destinationInput.addEventListener('input', function () {
    const urlValue = destinationInput.value.trim();
    const isValidURL = urlPattern.test(urlValue);

    if (urlValue === "") {
        errorMessage.classList.remove('show'); // Hide error message
        submitButton.disabled = true;
        errorMessage.textContent = defaultErrorText;
    } else if (isValidURL && (urlValue.startsWith('http://') || urlValue.startsWith('https://'))) {
        errorMessage.classList.remove('show'); // Hide error message
        errorMessage.style.maxHeight = '0'; // Collapse error message height
        submitButton.disabled = false; // Enable the submit button
    } else {
        errorMessage.classList.add('show'); // Show error message
        errorMessage.style.maxHeight = '50px'; // Extend error message height
        submitButton.disabled = true; // Disable the submit button
    }
});

document.getElementById('remove-url-button').addEventListener('click', function () {
    const container = document.getElementById('shortened-url-container');
    container.classList.remove('show'); // Remove 'show' class for animation
    setTimeout(() => {
        container.classList.add('hidden'); // Hide it after the animation
    }, 500); // Match this with the transition duration
});

// Copy shortened URL to clipboard
document.getElementById('copy-button').addEventListener('click', function () {
    const shortenedUrlElement = document.getElementById('shortened-url');
    const urlToCopy = shortenedUrlElement.innerText;

    navigator.clipboard.writeText(urlToCopy).then(() => {
        showNotification(); // Show notification
    }).catch(err => {
        console.error('Failed to copy: ', err);
    });
});

// Function to show notification
function showNotification() {
    notification.style.opacity = '1'; // Show notification
    setTimeout(() => {
        notification.style.opacity = '0'; // Hide after timeout
    }, 2000); // Show for 2 seconds
}

urlForm.onsubmit = async (e, token) => {
    e.preventDefault(); // Prevent the form from submitting normally

    let data = {
        destination: document.querySelector("input[name='destination']").value.trim(),
        redirect: parseInt(document.querySelector("input[name='redirect']:checked").value),
    }
    if (token !== null) {
        data.recaptcha = token;
    }
    errorMessage.classList.remove('show');

    await fetch(window.location.href, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    }).then((response) => {
        response.json().then((value) => {
            let error = value["error"];
            if (error !== undefined) {
                errorMessage.textContent = error;
                errorMessage.classList.add('show');
            } else {
                const shortenedURL = window.location.href + value["link"];
                // Show the shortened URL
                const container = document.getElementById('shortened-url-container');
                const shortenedUrlElement = document.getElementById('shortened-url');

                shortenedUrlElement.innerText = shortenedURL;
                shortenedUrlElement.href = shortenedURL;
                container.classList.remove('hidden');
                destinationInput.value = "";

                // Trigger the animation
                setTimeout(() => {
                    container.classList.add('show'); // Add the 'show' class for animation
                }, 10); // Slight delay to ensure the transition is recognized

            }

        }, rej_value => {
            console.log("rej", rej_value)
        });


    })
};
