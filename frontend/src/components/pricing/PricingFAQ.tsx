import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { HelpCircle } from "lucide-react";
import { useTranslation } from "react-i18next";

const FAQ_KEYS = ["1", "2", "3", "4", "5", "6", "7", "8"] as const;

export function PricingFAQ() {
  const { t } = useTranslation();

  return (
    <div className="bg-white rounded-lg p-6 shadow-md">
      <h3 className="flex items-center gap-2 font-semibold text-gray-900 text-lg mb-4">
        <HelpCircle className="w-5 h-5 text-blue-600" />
        {t("pricing.faq.title")}
      </h3>
      <Accordion type="single" collapsible className="w-full">
        {FAQ_KEYS.map((key) => (
          <AccordionItem key={key} value={`faq-${key}`}>
            <AccordionTrigger className="text-left text-sm font-medium text-gray-800 hover:no-underline">
              {t(`pricing.faq.q${key}`)}
            </AccordionTrigger>
            <AccordionContent className="text-sm text-gray-600 leading-relaxed">
              {t(`pricing.faq.a${key}`)}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}
