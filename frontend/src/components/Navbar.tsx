import React from 'react'
import { Logo } from '@/components/lib/icons';
import Link from 'next/link';

const Navbar = () => {
  return (
    <nav>
      <div className='flex'>
        <Link href="/" className='p-6 pb-4'>
          <div className='flex flex-col'>
            <Logo className='w-full' />
            <strong className='font-mono text-xl pt-1'>NewsInsights</strong>
          </div>
        </Link>
      </div>
      <hr className='border-gray-500'></hr>
    </nav>
  )
}

export default Navbar; 
