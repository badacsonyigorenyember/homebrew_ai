using System.Net;
using System.Net.Http.Json;

using HomebrewApp.Data;
using HomebrewApp.Features.Batches;

using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

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

            recipeId = await context.Recipes.Where(r => r.Process != null)
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
}
