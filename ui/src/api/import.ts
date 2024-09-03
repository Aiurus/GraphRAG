import { apiClient } from "./axios";

export async function importArticles() {
  try {
    const response = await apiClient.get("/import_articles/");
    return response.data;
  } catch (error) {
    console.log(error);
    throw error;
  }
}
