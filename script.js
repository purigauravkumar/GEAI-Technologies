(() => {
  const year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();

  const menuButton = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".main-nav");
  if (menuButton && nav) {
    menuButton.addEventListener("click", () => {
      const isOpen = menuButton.getAttribute("aria-expanded") === "true";
      menuButton.setAttribute("aria-expanded", String(!isOpen));
      nav.classList.toggle("is-open", !isOpen);
    });
    nav.querySelectorAll("a").forEach(link => link.addEventListener("click", () => {
      menuButton.setAttribute("aria-expanded", "false");
      nav.classList.remove("is-open");
    }));
  }

  const revealItems = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealItems.forEach(item => observer.observe(item));
  } else {
    revealItems.forEach(item => item.classList.add("is-visible"));
  }

  const modal = document.getElementById("certificate-modal");
  const modalTitle = document.getElementById("modal-title");
  const modalBody = document.getElementById("modal-body");
  let lastFocused = null;

  function closeModal() {
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
    modalBody.replaceChildren();
    if (lastFocused) lastFocused.focus();
  }

  document.querySelectorAll(".credential-card").forEach(card => {
    const button = card.querySelector(".certificate-open");
    const preview = card.querySelector(".credential-preview");
    function openCertificate() {
      lastFocused = button || preview;
      modalTitle.textContent = card.dataset.title || "Credential";
      modalBody.replaceChildren();
      if (card.dataset.textOnly === "true") {
        const content = document.createElement("div");
        content.className = "modal-text-card";
        const heading = document.createElement("h3");
        heading.textContent = "Computer Hardware Basics";
        const issuer = document.createElement("p");
        issuer.textContent = "Cisco Networking Academy";
        const note = document.createElement("p");
        note.textContent = "This course credential is listed in the GEAI Technologies learning record. The original certificate image and verification link have not yet been added.";
        content.append(heading, issuer, note);
        modalBody.append(content);
      } else {
        const img = document.createElement("img");
        img.src = card.dataset.certificate;
        img.alt = card.dataset.title + " certificate";
        img.addEventListener("error", () => {
          modalBody.textContent = "The certificate image could not be loaded. Check that the asset file is included in the website deployment.";
        });
        modalBody.append(img);
      }
      modal.classList.add("is-open");
      modal.setAttribute("aria-hidden", "false");
      document.body.classList.add("modal-open");
      modal.querySelector(".modal-close").focus();
    }
    if (button) button.addEventListener("click", openCertificate);
    if (preview) {
      preview.tabIndex = 0;
      preview.setAttribute("role", "button");
      preview.setAttribute("aria-label", "Preview " + (card.dataset.title || "credential"));
      preview.addEventListener("click", openCertificate);
      preview.addEventListener("keydown", event => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openCertificate();
        }
      });
    }
  });

  modal.querySelectorAll("[data-close-modal]").forEach(control => control.addEventListener("click", closeModal));
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && modal.classList.contains("is-open")) closeModal();
  });

  const sections = document.querySelectorAll("main section[id]");
  const navLinks = document.querySelectorAll('.main-nav a[href^="#"]');
  if ("IntersectionObserver" in window) {
    const sectionObserver = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          navLinks.forEach(link => link.classList.toggle("active", link.getAttribute("href") === "#" + entry.target.id));
        }
      });
    }, { rootMargin: "-35% 0px -55% 0px" });
    sections.forEach(section => sectionObserver.observe(section));
  }
})();