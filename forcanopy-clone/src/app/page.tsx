import { CallToAction } from "@/components/CallToAction";
import { CookieBanner } from "@/components/CookieBanner";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { Hero } from "@/components/Hero";
import { HowItWorks } from "@/components/HowItWorks";
import { Newsletter } from "@/components/Newsletter";
import { RecentTests } from "@/components/RecentTests";

export default function Home() {
  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded focus:bg-cta focus:px-4 focus:py-2 focus:text-onCta focus:ring-2 focus:ring-cta focus:ring-offset-2"
      >
        Skip to main content
      </a>

      <div className="relative flex min-h-screen flex-col overflow-x-clip">
        <Header />

        <main id="main-content" tabIndex={-1} className="flex-1 outline-none">
          <div className="overflow-x-clip">
            <Hero />
            <HowItWorks />
            <RecentTests />
            <CallToAction />
            <Newsletter />
          </div>
        </main>

        <Footer />
        <CookieBanner />
      </div>
    </>
  );
}
