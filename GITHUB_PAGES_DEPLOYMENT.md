# Deploying FINESE to GitHub Pages

This document explains how to deploy the FINESE frontend to GitHub Pages and set up the backend separately.

## Overview

GitHub Pages can only host static files (HTML, CSS, JavaScript), so the FINESE application needs to be split into two parts:
1. The frontend (React app) will be hosted on GitHub Pages
2. The backend (FastAPI app) must be hosted separately on a server that can run Python applications

## Step-by-Step Deployment Guide

### 1. Fork the Repository

First, fork this repository to your GitHub account.

### 2. Prepare the Backend API

The FINESE backend needs to be hosted separately. Here are some options:

#### Option A: Heroku (Free Tier Available)
1. Sign up for a Heroku account
2. Install the Heroku CLI
3. Create a new Heroku app
4. Deploy the backend code using Git or Docker

#### Option B: AWS, Azure, or Google Cloud
1. Create an account with your preferred cloud provider
2. Set up a compute instance or container service
3. Deploy the backend application

#### Option C: DigitalOcean, Linode, or Other VPS Providers
1. Create an account with your preferred provider
2. Set up a virtual server
3. Deploy the backend application

### 3. Configure CORS on Your Backend

Once your backend is deployed, you need to configure it to accept requests from your GitHub Pages domain:

In your backend's `backend/api/core/config.py` or wherever CORS is configured, update the allowed origins:

```python
# Add your GitHub Pages URL to the allowed origins
origins = [
    "https://your-username.github.io",  # Replace with your actual GitHub Pages URL
    "http://localhost:3000",  # For local development
    # Add other domains as needed
]
```

### 4. Configure Frontend API Endpoint

Update the frontend to point to your hosted backend API:

1. Create or update `frontend/.env.production`:
   ```
   REACT_APP_API_BASE_URL=https://your-backend-domain.com
   ```

2. Replace `https://your-backend-domain.com` with the actual URL of your deployed backend.

### 5. GitHub Actions Workflow

The repository includes a GitHub Actions workflow at `.github/workflows/deploy.yml` that will automatically deploy the frontend to GitHub Pages when you push to the main branch.

The workflow will:
1. Checkout your code
2. Install Node.js and dependencies
3. Build the React application with the correct path configuration
4. Deploy the built application to GitHub Pages

### 6. Enable GitHub Pages in Repository Settings

1. Go to your repository on GitHub
2. Click on "Settings"
3. Scroll down to the "Pages" section
4. Under "Source", select "GitHub Actions"

### 7. Update Package.json for Subdirectory Deployment (Optional)

If your GitHub Pages site is not served from the root (e.g., `https://your-username.github.io/repository-name`), the workflow already handles this by setting the PUBLIC_URL appropriately.

### 8. Test the Deployment

After pushing to the main branch, GitHub Actions will run the deployment workflow. You can monitor its progress in the "Actions" tab of your repository.

Once completed, your frontend will be available at `https://your-username.github.io/repository-name`.

## Troubleshooting

### Issue: API Requests Fail from GitHub Pages

**Solution:** Verify that:
1. Your backend allows requests from your GitHub Pages domain (CORS configuration)
2. The `REACT_APP_API_BASE_URL` is correctly set in the environment
3. Your backend is accessible via HTTPS (required for browsers when loading from HTTPS)

### Issue: Assets Not Loading Correctly

**Solution:** Make sure the `homepage` field in `package.json` is set correctly. For GitHub Pages, it should typically be `"."` to enable relative paths.

### Issue: Routing Issues (404s on Direct Navigation)

**Solution:** The `public/404.html` file in the frontend directory should handle client-side routing for GitHub Pages. Make sure it exists and contains the redirect script.

## Security Considerations

- Never expose sensitive API keys in the frontend code
- Ensure all communication between frontend and backend happens over HTTPS
- Implement proper authentication and authorization in your backend
- Sanitize all inputs on the backend to prevent injection attacks

## Performance Tips

- Minimize the size of datasets transferred between frontend and backend
- Implement caching strategies where appropriate
- Optimize your API responses to only send necessary data
- Consider implementing pagination for large datasets