import { useEffect, useRef } from 'react';
import { LogIn } from 'lucide-react';

interface GoogleSignInProps {
  onSuccess: (credential: string) => void;
  clientId: string;
}

export function GoogleSignIn({ onSuccess, clientId }: GoogleSignInProps) {
  const buttonRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Load Google Identity Services
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);

    script.onload = () => {
      if (window.google && buttonRef.current) {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: (response: { credential: string }) => {
            onSuccess(response.credential);
          },
        });

        window.google.accounts.id.renderButton(buttonRef.current, {
          theme: 'filled_black',
          size: 'large',
          width: 280,
          text: 'continue_with',
        });
      }
    };

    return () => {
      document.body.removeChild(script);
    };
  }, [clientId, onSuccess]);

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
