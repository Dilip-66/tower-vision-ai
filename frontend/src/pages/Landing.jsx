import { LandingHeader } from "../components/landing/LandingHeader";
import { Hero } from "../components/landing/Hero";
import { StatsBand } from "../components/landing/StatsBand";
import { HowItWorks } from "../components/landing/HowItWorks";
import { Showcase } from "../components/landing/Showcase";
import { QualitySection } from "../components/landing/QualitySection";
import { Features } from "../components/landing/Features";
import { CTASection } from "../components/landing/CTASection";
import { LandingFooter } from "../components/landing/LandingFooter";

export default function Landing() {
  return (
    <div className="lp-root min-h-screen">
      <LandingHeader />

      <main>
        <Hero />
        <StatsBand />
        <HowItWorks />
        <Showcase />
        <QualitySection />
        <Features />
        <CTASection />
      </main>

      <LandingFooter />
    </div>
  );
}
