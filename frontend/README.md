# Pro-Irrigation Frontend

Vue.js 3 frontend application for the Pro-Irrigation Home Assistant add-on.

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable Vue components
│   ├── views/          # Page-level components
│   ├── services/       # API client and services
│   ├── stores/         # Pinia state management
│   ├── router/         # Vue Router configuration
│   ├── App.vue         # Root component
│   ├── main.js         # Application entry point
│   └── style.css       # Global styles
├── index.html          # HTML template
├── vite.config.js      # Vite configuration
└── package.json        # Dependencies
```

## Development

### Install Dependencies

```bash
cd frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

The development server will start on `http://localhost:3000` with API proxy to `http://localhost:8000`.

### Build for Production

```bash
npm run build
```

This builds the application and outputs to `../backend/static` directory.

## Key Features

- **Vue 3 Composition API**: Modern Vue.js development
- **Vite**: Fast build tooling and HMR
- **Vue Router**: Client-side routing with hash mode for Ingress compatibility
- **Pinia**: State management with real-time polling
- **Axios**: HTTP client with error handling
- **Home Assistant Design**: Styling compatible with HA theme

## API Integration

The frontend communicates with the FastAPI backend through the API service (`src/services/api.js`).

In development, Vite proxies `/api` requests to the backend server.
In production, relative paths are used for Ingress compatibility.

## State Management

The Pinia store (`src/stores/irrigation.js`) manages:
- Pumps and zones data
- Global settings
- Real-time status polling (every 5 seconds)
- CRUD operations

## Routing

Routes are configured in `src/router/index.js`:
- `/` - Pumps Dashboard (home)
- `/pump/:pumpId/zones` - Zone Manager
- `/settings` - Global Settings

Hash mode is used for compatibility with Home Assistant Ingress.
