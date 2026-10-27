<script>
  const toast = document.querySelector("#toast");
  const copyButton = document.querySelector("#copy-btn");

  document.querySelector("#year").textContent =
    new Date().getFullYear();

  let toastTimer;

  function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");

    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.remove("show");
    }, 2200);
  }

  copyButton.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(
        "Welcome to Sitegen!"
      );
      showToast("Copied to clipboard!");
    } catch {
      showToast("Welcome to Sitegen!");
    }
  });
</script>

