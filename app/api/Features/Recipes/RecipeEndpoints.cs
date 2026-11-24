using HomebrewApp.Data;

using Microsoft.AspNetCore.Http.HttpResults;
using Microsoft.EntityFrameworkCore;

namespace HomebrewApp.Features.Recipes;

public record BrewableRecipeResponse(
    long Id,
    string StyleCode,
    string? StyleName,
    decimal? OG,
    decimal? FG,
    decimal? ABV,
    decimal? IBU,
    decimal BatchL,
    DateTime CreatedAt);

public static class RecipeEndpoints
{
    public static IEndpointRouteBuilder MapRecipeEndpoints(this IEndpointRouteBuilder endpoints)
    {
        endpoints.MapGroup("/api/recipes")
            .MapGet("/brewable", GetBrewableRecipes);
        return endpoints;
    }

    private static async Task<Ok<List<BrewableRecipeResponse>>> GetBrewableRecipes(
        AppDbContext context,
        CancellationToken cancellationToken)
    {
        var recipes = await context.Recipes.Where(r => r.Process != null)
            .OrderByDescending(r => r.CreatedAt)
            .Select(r => new BrewableRecipeResponse(r.Id, r.Style.Code, r.Style.Name, r.OG, r.FG, r.ABV, r.IBU,
                r.BatchL, r.CreatedAt))
            .ToListAsync(cancellationToken);

        return TypedResults.Ok(recipes);
    }
}
