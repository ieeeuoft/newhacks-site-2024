// Change navbar color on scroll
// Change height of navbar icon on scroll
$(document).scroll(function () {
    const $nav = $(".navbar");
    const $logo = $(".logoNav");

    $nav.toggleClass("navbarScrolled", $(this).scrollTop() > $nav.height());
    $logo.toggleClass("logoNavScrolled", $(this).scrollTop() > $nav.height());
});

$(document).ready(function () {
    // Materialize stuff
    $(".carousel").carousel({ dist: 0, padding: 600 });
    setInterval(function () {
        $(".carousel").carousel("next");
    }, 3000);

    $(".scrollspy").scrollSpy();
    $(".collapsible").collapsible();

    // Countdown stuff

    const now = new Date();
    let countDownDate;

    // Set the title based off what it's counting down to
    if (registrationOpenDate >= now) {
        countDownDate = registrationOpenDate;
        $("#countdownTitle").html("Registration Opens In");
    } else if (registrationCloseDate >= now) {
        countDownDate = registrationCloseDate;
        $("#countdownTitle").html("Registration Closes In");
    } else if (eventStartDate >= now) {
        countDownDate = eventStartDate;
        $("#countdownTitle").html("Event Starts In");
    }

    // Delete the entire countdown if event start date has passed
    if (eventStartDate < now) {
        $("#countdown").remove();
        $("#aboutText").removeClass("l7");
    } else {
        // Update the countdown every ten minute
        setInterval(setCounter(countDownDate), 600000);
    }
});

function setCounter(countDownDate) {
    const now = new Date();
    const distance = countDownDate - now;
    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
    const hours = Math.floor(distance / (1000 * 60 * 60));

    if (hours < 1) {
        const minutes = Math.floor(distance / (1000 * 60));
        // Change to show minutes on the website
        $("#day1").parent().remove();
        $("#day2").html(Math.floor(minutes / 10));
        $("#day3").html(minutes % 10);
        $("#countdownUnit").html(minutes === 1 ? "Minute" : "Minutes");
        return;
    }

    if (days < 2) {
        // Change to show hours on the website
        $("#day1").parent().remove();
        $("#day2").html(Math.floor(hours / 10));
        $("#day3").html(hours % 10);
        $("#countdownUnit").html(hours === 1 ? "Hour" : "Hours");
        return;
    }

    // Check if we need a third digit or not
    if (days > 99) {
        $("#day1").html(Math.floor(days / 100));
    } else {
        $("#day1").parent().remove();
    }

    $("#day2").html(Math.floor(days / 10) % 10);
    $("#day3").html(days % 10);
}
