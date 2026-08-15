import type { MetadataRoute } from "next";
import { site } from "@/lib/site";

// Requis par `output: export` : le fichier est produit au build.
export const dynamic = "force-static";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: `${site.url}/`,
      changeFrequency: "monthly",
      priority: 1,
    },
  ];
}
