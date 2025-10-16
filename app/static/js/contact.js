  const contactLink = document.getElementById('contactLink');
  const contactModal = document.getElementById('contactModal');
  const contactContainer = document.getElementById('contactFormContainer');
  const closeModal = document.getElementById('closeModal');

  contactLink.addEventListener('click', (e) => {
    e.preventDefault();
    fetch('contact.html')
      .then(res => res.text())
      .then(html => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const formWrapper = doc.querySelector('.form-wrapper');
        contactContainer.innerHTML = '';
        contactContainer.appendChild(formWrapper);
        contactModal.classList.remove('hidden');

        // re-initialize form script manually
        const form = contactContainer.querySelector('#form');
        const result = contactContainer.querySelector('#result');

        form.addEventListener("submit", function (e) {
          e.preventDefault();
          const formData = new FormData(form);
          const object = {};
          formData.forEach((value, key) => (object[key] = value));
          const json = JSON.stringify(object);
          result.innerHTML = "Please wait...";

          fetch("https://api.web3forms.com/submit", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Accept: "application/json"
            },
            body: json
          })
            .then(async (response) => {
              let json = await response.json();
              if (response.status === 200) {
                result.innerHTML = json.message;
                result.classList.remove("text-gray-400");
                result.classList.add("text-green-500");
              } else {
                result.innerHTML = json.message;
                result.classList.remove("text-gray-400");
                result.classList.add("text-red-500");
              }
            })
            .catch(() => {
              result.innerHTML = "Something went wrong!";
            })
            .then(() => {
              form.reset();
              setTimeout(() => {
                result.style.display = "none";
              }, 5000);
            });
        });
      });
  });

  closeModal.addEventListener('click', () => {
    contactModal.classList.add('hidden');
  });

  contactModal.addEventListener('click', (e) => {
    if (e.target === contactModal) {
      contactModal.classList.add('hidden');
    }
  });

