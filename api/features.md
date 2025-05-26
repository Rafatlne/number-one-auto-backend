Okay, based strictly on the requirements outlined in the "Full-Stack Interview Task: Personalized News Aggregator" PDF[cite: 1], and considering you'll be using `Djoser` with Django's built-in token-based authentication (`rest_framework.authtoken`), here is the list of necessary APIs:

### 1. User Authentication APIs (Leveraging Djoser)

* **User Registration**
    * **Endpoint (Djoser default):** `POST /auth/users/`
    * **Purpose:** To allow users to register. [cite: 1] The registration process should also set default news preferences (Countries: `["nz"]`, Sources: `["bbc-news", "cnn"]`, Keywords: `["car", "automobile"]`) for the new user[cite: 6]. This might require customizing Djoser's registration serializer or using signals.
* **User Login (Token Creation)**
    * **Endpoint (Djoser default for `authtoken`):** `POST /auth/token/login/`
    * **Purpose:** To allow registered users to securely log in using their email or username and password. [cite: 1]
* **User Logout (Token Destruction)**
    * **Endpoint (Djoser default for `authtoken`):** `POST /auth/token/logout/`
    * **Purpose:** To allow authenticated users to securely log out. (Implied by "securely log in" [cite: 1] and general security best practices for token-based systems).

### 2. User News Preferences APIs (Custom Implementation)

* **View User Preferences**
    * **Endpoint:** `GET /api/preferences`
    * **Purpose:** To allow authenticated users to view their current news preferences (countries, sources, keywords). [cite: 6]
* **Update User Preferences**
    * **Endpoint:** `PUT /api/preferences`
    * **Purpose:** To allow authenticated users to customize and update their news settings for country, sources, and keywords. [cite: 2, 6]

    *Highly Recommended Helper APIs for Preference Customization (to populate frontend selection options):*
    * **List Available Countries**
        * **Endpoint:** `GET /api/meta/countries`
        * **Purpose:** To provide the frontend with a list of selectable countries.
    * **List Available Sources**
        * **Endpoint:** `GET /api/meta/sources`
        * **Purpose:** To provide the frontend with a list of selectable news sources.

### 3. Personalized News Feed API (Custom Implementation)

* **Get Personalized News Feed**
    * **Endpoint:** `GET /api/news`
    * **Purpose:** To deliver a tailored and paginated news feed to the authenticated user based on their individual preferences. [cite: 1, 9]
    * **Features (via Query Parameters):**
        * **Pagination:** As required. [cite: 9]
        * **Search:** By keyword or title. [cite: 9]
        * **Filtering:** By source and publication date. [cite: 9]
    * **Article Data:** Each article in the response should include: Title, Summary, Source name, Source URL (to access original articles [cite: 3]), Publication date, and Image thumbnail (if available). [cite: 10]

**APIs covered by Djoser (implicitly useful for frontend but part of Djoser's standard set):**

* **Get Current User Details:**
    * **Endpoint (Djoser default):** `GET /auth/users/me/`
    * **Purpose:** Often needed by the frontend to display user-specific information after login.

**Important Note on Security:**
As stated in the document, "Secure all API endpoints, ensuring proper access control to user data and news." [cite: 5] This means all the custom APIs listed above (Preferences and News Feed) and the relevant Djoser endpoints must require authentication and proper authorization.