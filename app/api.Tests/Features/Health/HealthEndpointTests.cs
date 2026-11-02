using HomebrewApp.Features.Health;
using Microsoft.AspNetCore.Mvc.Testing;
using Newtonsoft.Json;

namespace HomebrewApp.Tests.Features.Health;

public class HealthEndpointTests(WebApplicationFactory<Program> factory) : IClassFixture<WebApplicationFactory<Program>>
{
    [Fact]
    public async Task HealthCheckTest()
    {
        var client = factory.CreateClient();

        var response = await client.SendAsync(new HttpRequestMessage(HttpMethod.Get, "/api/health"));

        var jsonString = await response.Content.ReadAsStringAsync();
        var healthResponse = JsonConvert.DeserializeObject<HealthResponse>(jsonString);

        Assert.NotNull(healthResponse);
        Assert.Equal("ok", healthResponse.Status);
    }
}
