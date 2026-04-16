/**
 * Telegram WebApp API wrapper
 * Minimal implementation for Telegram Mini Apps
 */

declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initData: string;
        initDataUnsafe: {
          user?: {
            id: number;
            first_name: string;
            last_name?: string;
            username?: string;
            language_code?: string;
          };
          query_id?: string;
          auth_date?: number;
        };
        ready: () => void;
        expand: () => void;
        close: () => void;
        enableClosingConfirmation: () => void;
        disableClosingConfirmation: () => void;
        sendData: (data: string) => void;
      };
    };
  }
}

const WebApp = typeof window !== "undefined" ? window.Telegram?.WebApp : undefined;

export const Telegram = {
  ready: () => {
    WebApp?.ready();
  },

  expand: () => {
    WebApp?.expand();
  },

  close: () => {
    WebApp?.close();
  },

  getUser: () => {
    return WebApp?.initDataUnsafe.user;
  },

  getInitData: () => {
    return WebApp?.initData;
  },
};

export default Telegram;
