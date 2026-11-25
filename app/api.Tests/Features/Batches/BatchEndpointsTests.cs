using System.Net;
using System.Net.Http.Json;

using HomebrewApp.Data;
using HomebrewApp.Features.Batches;

using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

using Npgsql;

namespace HomebrewApp.Tests.Features.Batches;

[Collection(nameof(ApiCollection))]
public class BatchEndpointsTests(ApiFactory factory)
{
    [Fact]
    public async Task CreateBatch_TwiceOnEmptyTable_NumbersOneAndTwo()
    {
        long recipeId;
        await using (var scope = factory.Services.CreateAsyncScope())
        {
            var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

            await context.Batches.ExecuteDeleteAsync();

            recipeId = await context.Recipes
                .Where(r => r.Process != null)
                .Select(r => r.Id)
                .SingleAsync();
        }

        var client = factory.CreateClient();

        var response1 = await client.PostAsJsonAsync("/api/batches",
            new CreateBatchRequest(recipeId, "Test name 1", new DateOnly(2026, 11, 25)));
        var response2 = await client.PostAsJsonAsync("/api/batches",
            new CreateBatchRequest(recipeId, "Test name 2", new DateOnly(2026, 11, 25)));

        Assert.Equal(HttpStatusCode.Created, response1.StatusCode);
        Assert.Equal(HttpStatusCode.Created, response2.StatusCode);

        var batchResponse1 = await response1.Content.ReadFromJsonAsync<BatchResponse>();
        var batchResponse2 = await response2.Content.ReadFromJsonAsync<BatchResponse>();

        Assert.Equal(1, batchResponse1?.Number);
        Assert.Equal(2, batchResponse2?.Number);
    }

    [Fact]
    public async Task CreateBatch_FromRecipe_CopiesItems()
    {
        long recipeId;
        IEnumerable<(long Id, long? IngredientId, string RawName, string Usage, decimal? TimeMin, decimal? Percentage,
            decimal Amount, string Unit)> recipeItems;
        await using (var scope = factory.Services.CreateAsyncScope())
        {
            var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

            await context.Batches.ExecuteDeleteAsync();

            recipeId = await context.Recipes
                .Where(r => r.Process != null)
                .Select(r => r.Id)
                .SingleAsync();

            var rawRecipeItems = await context.RecipeItems.Where(ri => ri.RecipeId == recipeId).ToListAsync();
            recipeItems = rawRecipeItems.Select(ri => (ri.Id, ri.IngredientId, ri.RawName, ri.Usage, ri.TimeMin,
                ri.Percentage, ri.Amount, ri.Unit));
        }

        var client = factory.CreateClient();

        var response = await client.PostAsJsonAsync("/api/batches",
            new CreateBatchRequest(recipeId, "Test name 1", new DateOnly(2026, 11, 25)));

        Assert.Equal(HttpStatusCode.Created, response.StatusCode);

        var batchResponse = await response.Content.ReadFromJsonAsync<BatchResponse>();

        Assert.NotNull(batchResponse);

        await using (var scope = factory.Services.CreateAsyncScope())
        {
            var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

            var rawBatchItems = await context.BatchItems
                .Where(bi => bi.BatchId == batchResponse.Id)
                .OrderBy(bi => bi.SourceItemId)
                .ToListAsync();
            var batchItems = rawBatchItems.Select(bi => ((long)bi.SourceItemId!, bi.IngredientId, bi.RawName, bi.Usage,
                bi.TimeMin, bi.Percentage, bi.Amount, bi.Unit));

            Assert.Equal(recipeItems, batchItems);

            await context.Batches.Where(b => b.Id == batchResponse.Id).ExecuteDeleteAsync();
        }
    }

    [Fact]
    public async Task CreateBatch_RecipeItemChangedAfterwards_BatchItemKeepsItsValue()
    {
        await using var scope = factory.Services.CreateAsyncScope();
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        long recipeId = await context.Recipes
            .Where(r => r.Process != null)
            .Select(r => r.Id)
            .SingleAsync();

        var client = factory.CreateClient();

        var response = await client.PostAsJsonAsync("/api/batches",
            new CreateBatchRequest(recipeId, "Test name 1", new DateOnly(2026, 11, 25)));

        Assert.Equal(HttpStatusCode.Created, response.StatusCode);

        var batchResponse = await response.Content.ReadFromJsonAsync<BatchResponse>();
        var item = batchResponse?.Items.First();
        Assert.NotNull(batchResponse);
        Assert.NotNull(item);
        Assert.NotNull(item.SourceItemId);

        await using var conn = new NpgsqlConnection(factory.AdminConnectionString);
        await conn.OpenAsync();
        await using var transaction = await conn.BeginTransactionAsync();

        await using (var command = new NpgsqlCommand("UPDATE app.recipe_item SET amount = amount + 1 WHERE id = @id;",
                         conn,
                         transaction))
        {
            command.Parameters.AddWithValue("id", item.SourceItemId);
            await command.ExecuteScalarAsync();
        }

        await using (var command = new NpgsqlCommand("SELECT amount FROM app.batch_item WHERE id = @id;",
                         conn,
                         transaction))
        {
            command.Parameters.AddWithValue("id", item.Id);
            var amount = await command.ExecuteScalarAsync();

            Assert.Equal(item.Amount, amount);
        }

        await transaction.RollbackAsync();

        await context.Batches.Where(b => b.Id == batchResponse.Id).ExecuteDeleteAsync();
    }

    [Fact]
    public async Task CreateBatch_RecipeWithoutProcess_Returns400Problem()
    {
        await using var scope = factory.Services.CreateAsyncScope();
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        var recipeId = await context.Recipes
            .Where(r => r.Process == null)
            .Select(r => r.Id)
            .SingleAsync();

        var client = factory.CreateClient();

        var response = await client.PostAsJsonAsync("/api/batches",
            new CreateBatchRequest(recipeId, "Test name 1", new DateOnly(2026, 11, 25)));
        var content = await response.Content.ReadFromJsonAsync<ProblemDetails>();

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        Assert.Equal("application/problem+json", response.Content.Headers.ContentType?.MediaType);
        Assert.Contains("process", content?.Detail);
    }

    [Fact]
    public async Task CreateBatch_UnknownRecipe_Returns404Problem()
    {
        var client = factory.CreateClient();

        var response = await client.PostAsJsonAsync("/api/batches",
            new CreateBatchRequest(long.MaxValue, "Test name 1", new DateOnly(2026, 11, 25)));

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
        Assert.Equal("application/problem+json", response.Content.Headers.ContentType?.MediaType);
    }

    [Fact]
    public async Task CreateBatch_WithoutNameAndBrewDate_Returns400PerField()
    {
        await using var scope = factory.Services.CreateAsyncScope();
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        var recipeId = await context.Recipes
            .Where(r => r.Process == null)
            .Select(r => r.Id)
            .SingleAsync();

        var client = factory.CreateClient();

        var response = await client.PostAsJsonAsync("/api/batches",
            new CreateBatchRequest(recipeId, null, null));
        var content = await response.Content.ReadFromJsonAsync<HttpValidationProblemDetails>();

        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        Assert.NotNull(content);
        Assert.Equal(2, content.Errors.Count);
        Assert.Contains("Name", content.Errors);
        Assert.Contains("BrewDate", content.Errors);
    }

    [Fact]
    public async Task ListBatches_AfterCreate_ContainsTheBatch()
    {
        await using var scope = factory.Services.CreateAsyncScope();
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        await context.Batches.ExecuteDeleteAsync();

        var recipeId = await context.Recipes
            .Where(r => r.Process != null)
            .Select(r => r.Id)
            .SingleAsync();

        var client = factory.CreateClient();

        var createResponse = await client.PostAsJsonAsync("/api/batches",
            new CreateBatchRequest(recipeId, "Test name 1", new DateOnly(2026, 11, 25)));

        Assert.Equal(HttpStatusCode.Created, createResponse.StatusCode);

        var createContent = await createResponse.Content.ReadFromJsonAsync<BatchResponse>();

        var listResponse = await client.GetFromJsonAsync<IEnumerable<BatchSummaryResponse>>("/api/batches");

        Assert.NotNull(createContent);
        Assert.NotNull(listResponse);
        Assert.Contains(createContent.Id, listResponse.Select(b => b.Id));

        await context.Batches.Where(b => b.Id == createContent.Id).ExecuteDeleteAsync();
    }
}
