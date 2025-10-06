import { FooterSection } from "@/components/layout/sections/footer";
import {Navbar} from "@/components/layout/navbar";
import {FeedbackSection} from "@/components/layout/sections/feedback";
export default function Home() {
    return (
        <div className="">
            <main>
                <Navbar />
                <FeedbackSection />
                <FooterSection />
            </main>
        </div>
    );
}
