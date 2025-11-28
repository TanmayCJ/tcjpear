import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Fetch version from PyPI API
    const response = await fetch('https://pypi.org/pypi/peargent/json', {
      next: { revalidate: 3600 } // Cache for 1 hour
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch from PyPI');
    }
    
    const data = await response.json();
    const version = data.info.version;
    
    // Format the version string
    const formattedVersion = `v${version} Public Beta`;
    
    return NextResponse.json({ 
      version: formattedVersion,
      rawVersion: version 
    });
  } catch (error) {
    console.error('Error fetching version from PyPI:', error);
    return NextResponse.json({ 
      version: 'v0.1 Public Beta',
      rawVersion: '0.1.0' 
    });
  }
}