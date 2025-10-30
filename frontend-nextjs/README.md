# PDF Processing Frontend - Next.js

Modern React frontend for the PDF Processing Application, built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

- ✅ **Type-Safe** - Full TypeScript implementation with type-safe API client
- ✅ **Modern React** - Built with Next.js 14 and React 18
- ✅ **Component-Based** - Reusable, well-structured components
- ✅ **Responsive Design** - Mobile-first approach with Tailwind CSS
- ✅ **State Management** - React hooks for clean state handling
- ✅ **Real-time Updates** - Auto-refresh for active jobs
- ✅ **Smooth Animations** - Custom animations for better UX
- ✅ **Error Handling** - Comprehensive error handling with user feedback

## Tech Stack

- **Next.js 14** - React framework with app router
- **React 18** - Latest React with hooks
- **TypeScript** - Type safety throughout
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls

## Project Structure

```
frontend-nextjs/
├── src/
│   ├── app/
│   │   ├── globals.css        # Global styles with Tailwind
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Main page with state management
│   ├── components/
│   │   ├── UploadSection.tsx  # File upload component
│   │   ├── JobCard.tsx        # Individual job display
│   │   └── ResultModal.tsx    # Result viewer modal
│   ├── lib/
│   │   └── api.ts             # API client functions
│   └── types/
│       └── index.ts           # TypeScript type definitions
├── public/                    # Static assets
├── Dockerfile                 # Production Docker image
├── package.json               # Dependencies
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.ts        # Tailwind configuration
└── next.config.js            # Next.js configuration
```

## Development

### Prerequisites

- Node.js 20+
- npm or yarn

### Install Dependencies

```bash
npm install
```

### Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Build for Production

```bash
npm run build
npm start
```

## Docker Deployment

### Build Image

```bash
docker build -t pdf-processor-frontend .
```

### Run Container

```bash
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  pdf-processor-frontend
```

### With Docker Compose

```bash
# From project root
docker-compose up --build
```

The frontend will be available at http://localhost:3000

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

## Components

### UploadSection

File upload interface with drag-and-drop support.

**Features:**
- Drag and drop PDFs
- Multiple file selection
- Parser selection (PyPDF, Gemini, Mistral)
- Upload progress indicator

### JobCard

Displays individual job information.

**Features:**
- Job status with color coding
- Job metadata (ID, filename, parser, timestamp)
- Action buttons (View Result, Check Status, Delete)
- Error message display

### ResultModal

Modal for viewing processing results.

**Features:**
- Full-screen modal overlay
- Page-by-page content display
- AI-generated summary
- Processing metrics
- Smooth animations

## API Client

Type-safe API client with full TypeScript support.

**Methods:**
- `uploadFiles(files, parser)` - Upload PDFs
- `getJobStatus(jobId)` - Check job status
- `getJobResult(jobId)` - Get processing result
- `listJobs()` - List all jobs
- `deleteJob(jobId)` - Delete job
- `healthCheck()` - Check API health

## State Management

Uses React hooks for state management:
- `useState` - Component state
- `useEffect` - Side effects and lifecycle
- `useCallback` - Memoized callbacks

## Styling

Built with Tailwind CSS utility classes:
- Responsive design with mobile-first approach
- Custom color scheme matching brand
- Smooth animations and transitions
- Consistent spacing and typography

## Type Safety

Full TypeScript implementation:
- Type definitions mirror backend Pydantic models
- API client with typed responses
- Component props with interfaces
- No `any` types used

## Benefits Over Vanilla HTML/JS

### Code Quality
- **Type Safety**: Catch errors at compile time
- **Component Reusability**: DRY principle
- **Better Structure**: Organized codebase
- **Modern Tooling**: ESLint, TypeScript, etc.

### Developer Experience
- **Hot Module Replacement**: Instant updates
- **TypeScript IntelliSense**: Auto-completion
- **Component Dev**: Easier debugging
- **Build Optimization**: Automatic code splitting

### User Experience
- **Faster Loading**: Optimized bundles
- **Better Performance**: React Virtual DOM
- **Smooth Animations**: CSS-in-JS support
- **SEO Ready**: Server-side rendering capable

### Maintainability
- **Clear Structure**: Component-based
- **Type Checking**: Prevents bugs
- **Easy Testing**: Component isolation
- **Scalable**: Add features easily

## Performance

- **Code Splitting**: Automatic by Next.js
- **Image Optimization**: Built-in Next.js feature
- **CSS Optimization**: Tailwind JIT compiler
- **Bundle Size**: Optimized production builds

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers

## Comparison: Vanilla vs Next.js

| Feature | Vanilla HTML/JS | Next.js/React |
|---------|----------------|---------------|
| **Type Safety** | ❌ None | ✅ Full TypeScript |
| **Component Reuse** | ❌ Manual | ✅ Built-in |
| **State Management** | ❌ Manual DOM | ✅ React Hooks |
| **Build Process** | ❌ None | ✅ Optimized |
| **Hot Reload** | ❌ No | ✅ Yes |
| **Code Splitting** | ❌ Manual | ✅ Automatic |
| **SEO** | ⚠️ Limited | ✅ SSR Ready |
| **Testing** | ⚠️ Difficult | ✅ Easy |
| **Maintainability** | ⚠️ Hard | ✅ Easy |
| **Learning Curve** | ✅ Low | ⚠️ Medium |

## Future Enhancements

- [ ] Server-side rendering for SEO
- [ ] Progressive Web App (PWA)
- [ ] Real-time WebSocket updates
- [ ] Keyboard shortcuts
- [ ] Dark mode toggle
- [ ] File preview before upload
- [ ] Download results as files
- [ ] Batch operations
- [ ] Advanced filtering/search
- [ ] User preferences persistence

## License

MIT

---

**Built with ❤️ using Next.js and React**
