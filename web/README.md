# Portfolio Analytics Web

A React + TypeScript frontend application for tracking and analyzing investment portfolio performance.

## Features

- **Dashboard**: View portfolio analytics including metrics, risk vs return charts, asset allocation, and benchmark comparisons
- **Holdings Management**: Add, edit, delete holdings, and bulk import via CSV upload
- **Session-based**: No authentication required - each browser session maintains its own portfolio
- **Responsive Design**: Mobile-first design that works across all device sizes
- **Dark Mode**: Automatic dark mode support based on system preferences

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Recharts** - Data visualization
- **CSS Modules** - Scoped styling

## Project Structure

```
web/
├── src/
│   ├── pages/
│   │   ├── dashboard/           # Dashboard page and analytics
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── useDashboardData.ts
│   │   │   ├── dashboardApi.ts
│   │   │   └── components/
│   │   │       ├── MetricsCards.tsx
│   │   │       ├── RiskReturnChart.tsx
│   │   │       ├── AssetAllocationChart.tsx
│   │   │       └── BenchmarkComparison.tsx
│   │   └── holdings/            # Holdings management page
│   │       ├── HoldingsPage.tsx
│   │       ├── useHoldingsState.ts
│   │       ├── holdingsApi.ts
│   │       └── components/
│   │           ├── HoldingsTable.tsx
│   │           ├── AddHoldingForm.tsx
│   │           ├── EditHoldingModal.tsx
│   │           └── CsvUpload.tsx
│   ├── shared/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── Layout.tsx
│   │   │   ├── Navigation.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── ErrorMessage.tsx
│   │   ├── hooks/               # Shared hooks
│   │   │   └── useSession.ts
│   │   ├── api/                 # API client
│   │   │   └── client.ts
│   │   └── types/               # TypeScript types
│   │       └── index.ts
│   ├── App.tsx                  # Root component with routing
│   ├── main.tsx                 # Entry point
│   └── index.css                # Global styles and CSS variables
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Architecture

The application follows a **page-based feature organization** with clear **view-state separation**:

- **Pages**: Each page is a self-contained feature with its own components, API functions, and state management
- **View Layer**: React components focused on rendering UI
- **State Layer**: Custom hooks manage business logic, API calls, and state
- **API Layer**: Dedicated API functions for each feature

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running at http://localhost:8001

### Installation

```bash
# Navigate to web directory
cd web

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

The application will be available at http://localhost:3001.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | `http://localhost:8001` |

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |

## API Integration

The frontend communicates with the backend API at the configured `VITE_API_URL`. Key endpoints:

### Sessions
- `POST /sessions` - Create a new session
- `GET /sessions/{id}` - Get session info

### Holdings
- `GET /holdings?session_id={id}` - List holdings
- `POST /holdings` - Create holding
- `PUT /holdings/{id}` - Update holding
- `DELETE /holdings/{id}` - Delete holding
- `POST /holdings/upload` - Bulk import from CSV

### Analytics
- `GET /analytics?session_id={id}` - Get portfolio analytics

## Session Management

Sessions are created automatically and stored in localStorage. Each session has its own isolated set of holdings. No authentication is required.

## Styling

The application uses CSS Modules for component-scoped styling with global CSS custom properties for theming:

- **Colors**: Primary, success, error, warning palettes
- **Typography**: System font stack
- **Spacing**: Consistent spacing scale
- **Dark Mode**: Automatic via `prefers-color-scheme`

## Responsive Breakpoints

| Breakpoint | Min Width | Target |
|------------|-----------|--------|
| Mobile | 0px | Small phones |
| Small | 480px | Large phones |
| Tablet | 768px | Tablets |
| Desktop | 1024px | Laptops |
| Large | 1280px | Desktops |

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Follow the existing code patterns and architecture
2. Write TypeScript with proper types
3. Ensure responsive design works on all breakpoints
4. Test loading, error, and empty states
5. Keep components small and focused

## License

MIT
