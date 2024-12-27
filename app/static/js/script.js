document.addEventListener("DOMContentLoaded", () => {
    const searchForm = document.getElementById("searchForm");

    // Handle search form submission
    searchForm.addEventListener("submit", (event) => {
        event.preventDefault(); // Prevent default form submission

        const searchInput = document.getElementById("search");
        const query = searchInput.value.trim();

        if (!query) {
            alert("Please enter a search term.");
            return;
        }

        // Redirect to the results page with the query as a parameter
        window.location.href = `/results?query=${encodeURIComponent(query)}`;
    });

    // Navigation handlers for other links/buttons
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
    navigateTo("addArticle", "/add_articles");

    navigateTo("addHomeLink" , "http://127.0.0.1:5000/")
});
