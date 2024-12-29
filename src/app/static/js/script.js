document.addEventListener("DOMContentLoaded", () => {
    const searchForm = document.getElementById("searchForm");

    searchForm.addEventListener("submit", (event) => {
        event.preventDefault(); 

        const searchInput = document.getElementById("search");
        const query = searchInput.value.trim();

        if (!query) {
            alert("Please enter a search term.");
            return;
        }

        window.location.href = `/results?query=${encodeURIComponent(query)}`;
    });

    const navigateTo = (selector, route) => {
        const element = document.getElementById(selector);
        if (element) {
            element.addEventListener("click", (event) => {
                event.preventDefault();
                window.location.href = route;
            });
        }
    };

    // Redirect home
    navigateTo("homeLink", "/");

    // Redirect to Add Articles
    navigateTo("addArticle", "http://127.0.0.1:5001/");

    navigateTo("addHomeLink" , "http://127.0.0.1:5000/")
});
