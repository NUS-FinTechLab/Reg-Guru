"use client";
import {Card, CardContent, CardFooter, CardHeader,} from "@/components/ui/card";
import {Building2, Mail, Phone} from "lucide-react";
import {useForm} from "react-hook-form";
import {z} from "zod";
import {zodResolver} from "@hookform/resolvers/zod";

import {Form, FormControl, FormField, FormItem, FormLabel, FormMessage,} from "@/components/ui/form";
import {Input} from "@/components/ui/input";
import {Button} from "@/components/ui/button";
import {Textarea} from "@/components/ui/textarea";

const formSchema = z.object({
    firstName: z.string().min(2).max(255),
    lastName: z.string().min(2).max(255),
    email: z.string().email(),
    message: z.string(),
});

export const FeedbackSection = () => {
    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            firstName: "",
            lastName: "",
            email: "",
            message: "",
        },
    });

    function onSubmit(values: z.infer<typeof formSchema>) {
        const { firstName, lastName, email, message } = values;
        console.log(values);
        window.location.href = `mailto:mail@example.com?body=Hello I am ${firstName} ${lastName}, my Email is ${email}. %0D%0A${message}`;
    }

    return (
        <section id="contact" className="container py-24 sm:py-32 px-6 lg:px-24 px-6 w-full mx-auto">
            <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                    <div className="mb-4">
                        <h2 className="text-primary mb-2 tracking-wider uppercase font-mono text-xs">
                            Feedback
                        </h2>

                        <h2 className="text-3xl md:text-4xl font-semibold">Your suggestion is valuable for us!</h2>
                    </div>
                    <p className="mb-8 text-muted-foreground lg:w-5/6">
                        We put our users first and learn from our mistakes. Please report any bugs, give suggestions, request a feature.
                    </p>

                    <div className="flex flex-col gap-4">
                        <div>
                            <div className="flex gap-2 mb-1">
                                <Building2 />
                                <div className="font-bold">Find us</div>
                            </div>

                            <div>Lorem ipsum dolor sit amet consectetur adipisicing elit.</div>
                        </div>

                        <div>
                            <div className="flex gap-2 mb-1">
                                <Phone />
                                <div className="font-bold">Call us</div>
                            </div>

                            <div>+1 (123) 123-4567</div>
                        </div>

                        <div>
                            <div className="flex gap-2 mb-1">
                                <Mail />
                                <div className="font-bold">Mail US</div>
                            </div>

                            <div>example@example.com</div>
                        </div>

                        <div>
                        </div>
                    </div>
                </div>

                <Card className="bg-muted/60 dark:bg-[#171717]">
                    <CardHeader className="text-primary text-2xl"> </CardHeader>
                    <CardContent>
                        <Form {...form}>
                            <form
                                onSubmit={form.handleSubmit(onSubmit)}
                                className="grid w-full gap-4"
                            >
                                <div className="flex flex-col md:!flex-row gap-8">
                                    <FormField
                                        control={form.control}
                                        name="firstName"
                                        render={({ field }) => (
                                            <FormItem className="w-full">
                                                <FormLabel>First Name</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="Your first name" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                    <FormField
                                        control={form.control}
                                        name="lastName"
                                        render={({ field }) => (
                                            <FormItem className="w-full">
                                                <FormLabel>Last Name</FormLabel>
                                                <FormControl>
                                                    <Input placeholder="You last name" {...field} />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>

                                <div className="flex flex-col gap-1.5">
                                    <FormField
                                        control={form.control}
                                        name="email"
                                        render={({ field }) => (
                                            <FormItem>
                                                <FormLabel>Email</FormLabel>
                                                <FormControl>
                                                    <Input
                                                        type="email"
                                                        placeholder="Enter your email address"
                                                        {...field}
                                                    />
                                                </FormControl>
                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>

                                <div className="flex flex-col gap-1.5">
                                    <FormField
                                        control={form.control}
                                        name="message"
                                        render={({ field  }:{field:any}) => (
                                            <FormItem>
                                                <FormLabel>Message</FormLabel>
                                                <FormControl>
                                                    <Textarea
                                                        rows={5}
                                                        placeholder="Your feedback..."
                                                        className="resize-none"
                                                        {...field}
                                                    />
                                                </FormControl>

                                                <FormMessage />
                                            </FormItem>
                                        )}
                                    />
                                </div>

                                <Button className="mt-4 cursor-pointer">Send message</Button>
                            </form>
                        </Form>
                    </CardContent>

                    <CardFooter></CardFooter>
                </Card>
            </section>
        </section>
    );
};
