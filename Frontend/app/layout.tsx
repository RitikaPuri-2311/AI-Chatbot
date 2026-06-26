import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "@/components/ThemeProvider";
import { Toaster } from "react-hot-toast";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Chatbot",
  description: "Your AI assistant powered by Gemini",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} 
        h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col">
        <ThemeProvider>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                fontSize: '13px',
                borderRadius: '10px',
                padding: '12px 16px',
              },
              success: {
                style: {
                  background: '#E1F5EE',
                  color: '#085041',
                  border: '0.5px solid #5DCAA5',
                },
              },
              error: {
                style: {
                  background: '#FAECE7',
                  color: '#712B13',
                  border: '0.5px solid #F0997B',
                },
                duration: 6000,
              },
            }}
          />
        </ThemeProvider>
      </body>
    </html>
  )
}