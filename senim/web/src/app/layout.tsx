import type { Metadata, Viewport } from "next";
import { Google_Sans } from "next/font/google";
import { cookies } from "next/headers";
import { Providers } from "@/components/Providers";
import { LANG_COOKIE, parseLang } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import "./globals.css";

// Google Sans is the only typeface. Its cyrillic-ext subset carries the Kazakh letters
// (ә, ғ, қ, ң, ө, ұ, ү, һ, і); numbers use tabular figures instead of a separate mono font.
const googleSans = Google_Sans({
  variable: "--font-google-sans",
  subsets: ["latin", "cyrillic", "cyrillic-ext"],
  // next/font has no metrics for Google Sans, so use a plain system fallback while it loads.
  adjustFontFallback: false,
  fallback: ["system-ui", "sans-serif"],
});

export const metadata: Metadata = {
  title: "SENIM, полиграф для ответов ИИ",
  description:
    "Вставьте ответ ChatGPT или Gemini. Пять независимых датчиков проверят каждое утверждение и покажут доказательства.",
};

export const viewport: Viewport = {
  themeColor: "#f6f7f5",
  colorScheme: "light",
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const lang = parseLang((await cookies()).get(LANG_COOKIE)?.value);
  return (
    <html lang={lang} className={cn("antialiased", googleSans.variable)}>
      <body className="flex min-h-[100dvh] flex-col">
        <Providers lang={lang}>{children}</Providers>
      </body>
    </html>
  );
}
