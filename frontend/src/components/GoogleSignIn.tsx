import { useEffect, useRef } from 'react';
import { LogIn } from 'lucide-react';

interface GoogleSignInProps {
  onSuccess: (credential: string) => void;
  clientId: string;
  onError?: (error: string) => void;
}

export function GoogleSignIn({ onSuccess, clientId, onError }: GoogleSignInProps) {
  const buttonRef = useRef<HTMLDivElement>(null);
  const googleInitialized = useRef(false);

  useEffect(() => {
    // Only load and initialize Google Sign-In once
    if (googleInitialized.current) return;
    
    // Load Google Identity Services
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);

    script.onload = () => {
      if (window.google && buttonRef.current) {
        // Debug info
        const debugInfo = {
          origin: window.location.origin,
          host: window.location.host,
          clientId: clientId ? clientId.substring(0, 20) + '...' : 'MISSING'
        };
        
        console.log('🔍 Google Sign-In Debug Info:', debugInfo);
        console.log('🔍 Using client ID:', clientId);
        
        if (!clientId) {
          console.error('❌ ERROR: Client ID is missing! Check your .env file');
          onError?.('Client ID not configured');
          return;
        }

        try {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: (response: { credential: string }) => {
              console.log('✅ Google Sign-In successful, token received');
              onSuccess(response.credential);
            },
            error_callback: () => {
              console.error('❌ Google Sign-In error callback triggered');
              onError?.('Google Sign-In failed');
            }
          });

          window.google.accounts.id.renderButton(buttonRef.current, {
            theme: 'filled_black',
            size: 'large',
            width: 280,
            text: 'signin_with',
          });
          
          console.log('✅ Google Sign-In button rendered successfully');
          googleInitialized.current = true;
        } catch (err) {
          console.error('❌ Error initializing Google Sign-In:', err);
          onError?.(err instanceof Error ? err.message : 'Failed to initialize Google Sign-In');
        }
      } else {
        console.error('❌ Google library not loaded or button ref not available');
      }
    };

    script.onerror = () => {
      console.error('❌ Failed to load Google Sign-In script');
      onError?.('Failed to load Google Sign-In library');
    };

    return () => {
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, [clientId]); // Only depend on clientId, not the callbacks

  return (
    <div className="flex flex-col items-center gap-4">
      <div ref={buttonRef} />
      <p className="text-xs text-gray-500 text-center max-w-xs">
        Sign in to save your journal entries securely
      </p>
    </div>
  );
}

// Fallback button when Google script fails to load
export function GoogleSignInFallback({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-3 px-6 py-3 bg-white text-gray-900 rounded-lg
        hover:bg-gray-100 transition-colors font-medium"
    >
      <LogIn className="w-5 h-5" />
      Sign in with Google
    </button>
  );
}

// Type declaration for Google Identity Services
declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
            error_callback?: () => void;
          }) => void;
          renderButton: (
            element: HTMLElement,
            options: {
              theme: string;
              size: string;
              width?: number;
              text?: string;
            }
          ) => void;
          prompt: () => void;
        };
      };
    };
  }
}
