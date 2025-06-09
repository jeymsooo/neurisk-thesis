import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="w-full bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="text-xl font-extrabold tracking-tight text-black">Neurisk</div>
        <div className="flex gap-6 text-gray-700 font-medium">
          <Link href="/register" className="hover:text-black transition-colors">Test</Link>
          <Link href="/search" className="hover:text-black transition-colors">Search</Link>
        </div>
      </div>
    </nav>
  );
} 