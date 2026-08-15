import type { MetadataRoute } from "next";
import { site } from "@/lib/site";

// Requis par `output: export` : le fichier est produit au build.
export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: `${site.url}/sitemap.xml`,
  };
}
