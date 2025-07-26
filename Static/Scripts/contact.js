// Handle contact form submission
document
  .getElementById("contactForm")
  ?.addEventListener("submit", function (e) {
    e.preventDefault();

    // Get form values
    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const message = document.getElementById("message").value;
    const submitButton = document.querySelector(".submit-button");
    submitButton.innerText = "sending...";
    submitButton.disabled = true;
    fetch("https://formsubmit.co/ajax/your@email.com", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ name, email, message }),
    })
      .then((response) => response.json())
      .then((data) => console.log(data))
      .catch((error) => console.log(error))
      .finally(() => {
        // Show success message
        alert("Thank you for your message! We will get back to you soon.");
        submitButton.disabled = false;
        submitButton.innerText = "Send Message";
      });
    // Reset form
    this.reset();
  });
