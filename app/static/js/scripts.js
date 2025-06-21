
window.addEventListener('DOMContentLoaded', event => {

    // Toggle the side navigation
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    if (sidebarToggle) {
        // Uncomment Below to persist sidebar toggle between refreshes
        // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
        //     document.body.classList.toggle('sb-sidenav-toggled');
        // }
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            document.body.classList.toggle('sb-sidenav-toggled');
            localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
        });
    }

});


// Automatically remove flash messages after 3 seconds
setTimeout(function() {
    const flashMessages = document.getElementById('flash-messages');
    if (flashMessages) {
        flashMessages.innerHTML = ''; // Remove the messages from DOM
    }
}, 4000); // Adjust the timeout duration (3000ms = 3 seconds)


// OTP varification

document.getElementById("register-btn").addEventListener("click", function() {
    // Hide the registration form and show the OTP section
    document.getElementById("registration-form").style.display = "none";
    document.getElementById("otp-section").style.display = "block";
    
    // Start the timer
    startTimer();
});

// Timer functionality
var timeLeft = 60; // 5 minutes in seconds

function startTimer() {
    var timerElement = document.getElementById("timer");
    var interval = setInterval(function() {
        var minutes = Math.floor(timeLeft / 60);
        var seconds = timeLeft % 60;
        timerElement.textContent = formatTime(minutes) + ":" + formatTime(seconds);
        timeLeft--;

        if (timeLeft < 0) {
            clearInterval(interval);
            alert("OTP expired. Redirecting to register page...");
            // Redirect to the register page
            window.location.href = "/register_page"; // Change this to the actual register page URL
        }
    }, 1000);
}

function formatTime(time) {
    return time < 10 ? "0" + time : time;
}
function formatTime(time) {
    return time < 10 ? "0" + time : time;
}

window.onload = startTimer;



// Js For Charts


