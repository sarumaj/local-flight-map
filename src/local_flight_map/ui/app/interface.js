/**
 * Main interface initialization script
 * This script handles the initial setup of the map interface and cleanup on page unload
 * It uses an IIFE (Immediately Invoked Function Expression) to avoid polluting the global scope
 */
(function () {
  /**
   * Initialize the map interface when the DOM is ready
   * Dispatches a 'mapElementReady' event with the map element ID
   */
  document.addEventListener("DOMContentLoaded", function () {
    const mapElement = document.querySelector(".folium-map");
    if (mapElement) {
      window.dispatchEvent(new CustomEvent("mapElementReady", {
        detail: { mapId: mapElement.id }
      }));
    }

    // Add social media links
    const socialLinks = document.createElement('div');
    socialLinks.className = 'social-links';

    // GitHub link
    for (const link of [
      {
        src: 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png',
        href: 'https://github.com/sarumaj/local-flight-map',
        alt: 'GitHub'
      },
      {
        src: 'https://cdn.jsdelivr.net/gh/devicons/devicon/icons/linkedin/linkedin-original.svg',
        href: 'https://www.linkedin.com/in/dawid-ciepiela/',
        alt: 'LinkedIn'
      }
    ]) {
      const linkElement = document.createElement('a');
      linkElement.href = link.href;
      linkElement.className = 'social-link';
      linkElement.target = '_blank';
      linkElement.rel = 'noopener noreferrer';
      linkElement.innerHTML = `<img src="${link.src}" alt="${link.alt}">`;
      socialLinks.appendChild(linkElement);
    }

    document.body.appendChild(socialLinks);
  });

  /**
   * Cleanup handler for page refresh/reload
   * Ensures proper cleanup of the draggable bounding box before page unload
   */
  window.addEventListener("beforeunload", function () {
    if (window.draggableBBox) {
      window.draggableBBox.destroy();
    }
  });

  /**
   * Check session state and show cookie consent banner if necessary
   * @param {void}
   * @returns {Promise<boolean>} True if authenticated and has cookie consent, false otherwise
   */
  async function checkSessionState() {
    try {
      const response = await fetch('/auth/status');
      if (response.ok) {
        const data = await response.json();
        // Only return true if both authenticated and has cookie consent
        return data.authenticated && data.cookie_consent;
      }
      return false;
    } catch (error) {
      console.error('Error checking session state:', error);
      return false;
    }
  }

  /**
   * Show cookie consent banner if necessary
   * @param {void}
   * @returns {void}
   */
  async function showCookieConsent() {
    const isAuthenticated = await checkSessionState();
    if (!isAuthenticated) {
      const modalOverlay = document.createElement('div');
      modalOverlay.id = 'cookie-consent-modal';

      const modalContent = document.createElement('div');
      modalContent.className = 'modal-content';

      const title = document.createElement('h2');
      title.textContent = 'Cookie Consent Required';

      const message = document.createElement('p');
      message.textContent = 'This flight map application requires cookies to function properly. ' +
        'Without cookies, the application cannot maintain your session and provide the necessary functionality.';

      const buttonContainer = document.createElement('div');
      buttonContainer.className = 'button-container';

      const acceptButton = document.createElement('button');
      acceptButton.textContent = 'Accept Cookies';
      acceptButton.className = 'accept-button';

      const declineButton = document.createElement('button');
      declineButton.textContent = 'Decline';
      declineButton.className = 'decline-button';

      acceptButton.onclick = async () => {
        try {
          const response = await fetch('/auth/cookie-consent', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ consent: true })
          });

          if (response.ok) {
            modalOverlay.remove();
            window.location.reload();
          }
        } catch (error) {
          console.error('Error setting cookie consent:', error);
        }
      };

      declineButton.onclick = () => {
        if (confirm('Are you sure you want to decline cookies? The flight map will not work without cookies enabled.')) {
          modalOverlay.remove();
          window.history.back();
        }
      };

      buttonContainer.appendChild(acceptButton);
      buttonContainer.appendChild(declineButton);

      modalContent.appendChild(title);
      modalContent.appendChild(message);
      modalContent.appendChild(buttonContainer);
      modalOverlay.appendChild(modalContent);
      document.body.appendChild(modalOverlay);
    }
  }

  // Show cookie consent banner when the page loads
  document.addEventListener('DOMContentLoaded', showCookieConsent);
})();


