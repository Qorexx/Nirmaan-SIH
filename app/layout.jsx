import './globals.css';

export const metadata = {
  title: 'Person 3 — Duplicate & Similarity Detection AI (MPLADS)',
  description: 'AI-powered duplicate project & similarity detection system for MPLADS Scheme implementation',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet" />
      </head>
      <body class="bg-slate-50 text-slate-900 font-['Inter'] antialiased">
        {children}
      </body>
    </html>
  );
}
