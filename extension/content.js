chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log("Message received in content.js:", request);
  if (request.action === "getVideoUrl") {
    const videoElement = document.querySelector("video");
    if (videoElement) {
      console.log("Video element found, sending URL:", videoElement.src);
      sendResponse({ url: videoElement.src });
    } else {
      const embedElement = document.querySelector("embed");
      if (embedElement) {
        console.log("Embed element found, sending URL:", embedElement.src);
        sendResponse({ url: embedElement.src });
      } else {
        console.log("Video element not found");
        sendResponse({ url: null });
      }
    }
  }
  return true; // Keep this line to indicate the response was sent correctly
});
