import { Separator } from "@/components/ui/separator";
import { ChevronsDownIcon } from "lucide-react";
import Link from "next/link";
import Image from "next/image";
import React from "react";

export const FooterSection = () => {
  return (
    <footer id="footer" className="container py-24 sm:py-8 px-6 lg:px-24 px-6 w-full mx-auto">
      <div className="">
        <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-x-12 gap-y-8 py-4">
          <div className="col-span-full xl:col-span-2">
            <Link href="/" className="font-bold text-lg flex items-center">
              <Image
                  src={"/logo.png"}
                  className="w-10 mr-2 h-auto transition-transform duration-300 hover:scale-110"
                  width={400}
                  height={400}
                  alt="logo"
              />
              <span className="transition-colors font-bold font-mono uppercase duration-300 hover:text-primary">reg-guru</span>
            </Link>
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="font-bold text-lg">Contact</h3>
            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                Github
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                Twitter
              </Link>
            </div>

            <div>
              <Link href="/contact" className="opacity-60 hover:opacity-100">
                Say Hello!
              </Link>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="font-bold text-lg">Platforms</h3>
            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                iOS
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                Android
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                Web
              </Link>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="font-bold text-lg">Help</h3>

            <div>
              <Link href="/terms-and-conditions" className="opacity-60 hover:opacity-100">
                Terms & Conditions
              </Link>
            </div>
            <div>
              <Link href="/privacy-policy" className="opacity-60 hover:opacity-100">
                Privacy Policy
              </Link>
            </div>
            <div>
              <Link href="/feedback" className="opacity-60 hover:opacity-100">
                Feedback
              </Link>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <h3 className="font-bold text-lg">Socials</h3>
            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                Twitch
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                Discord
              </Link>
            </div>

            <div>
              <Link href="#" className="opacity-60 hover:opacity-100">
                Dribbble
              </Link>
            </div>
          </div>
        </div>

        <Separator className="my-2" />
        <section className="py-4">
          <h3 className="">
            All Rights Reserved &copy;
            <Link
              target="_blank"
              href="https://github.com/leoMirandaa"
              className="text-primary transition-all border-primary hover:border-b-2 ml-1"
            >
              Reg-Guru
            </Link>
          </h3>
        </section>
      </div>
    </footer>
  );
};
