
import {HeroSection} from "@/components/layout/sections/hero";
import { ContactSection } from "@/components/layout/sections/contact";
import { FeaturesSection } from "@/components/layout/sections/features";
import { FooterSection } from "@/components/layout/sections/footer";
import {Navbar} from "@/components/layout/navbar";
import { HowItWorksSection} from "@/components/layout/sections/howItWorks";
export default function Home() {
  return (
    <div className="">
      <main>
          <Navbar />
          <HeroSection />
          <HowItWorksSection/>
          <FeaturesSection />
          <ContactSection />
          <FooterSection />
      </main>
    </div>
  );
}
