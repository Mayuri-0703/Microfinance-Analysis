let slideIndex = 0;
showSlides();

function showSlides() {
    let slides = document.querySelectorAll(".slide");
    for (let i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }
    slideIndex++;
    if (slideIndex > slides.length) { slideIndex = 1; }
    slides[slideIndex - 1].style.display = "block";
    setTimeout(showSlides, 5000); // Change image every 5 seconds
}

document.addEventListener("DOMContentLoaded", showSlides);

// Run the function on page load
showSlides();

document.addEventListener("DOMContentLoaded", function() {
    let greetingSection = document.querySelector(".greeting");
    
    // Add 'show' class after 0.5s for smooth fade-in effect
    setTimeout(() => {
        greetingSection.classList.add("show");
    }, 500);
});

    