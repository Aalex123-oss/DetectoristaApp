import type { Metadata } from 'next';

import './globals.css';

export const metadata: Metadata = {
  title: 'Detectorista Web GIS — LiDAR & Historical Intelligence',
  description:
    'Professional Web GIS for LiDAR visualisation, historical cartography comparison and automated archaeological research.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-panel text-slate-200 antialiased">{children}</body>
    </html>
  );
}
