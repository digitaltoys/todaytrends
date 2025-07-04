import { Grid, Card } from '../layout';

interface StatisticsCardsProps {
  totalCount: number;
  tweetsLength: number;
}

export function StatisticsCards({ totalCount, tweetsLength }: StatisticsCardsProps) {
  return (
    <Grid cols={3} data-name="statistics-cards">
      <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white" data-name="total-tweets-card">
        <h3 className="text-lg font-semibold mb-2">총 수집된 트윗</h3>
        <p className="text-3xl font-bold">{totalCount.toLocaleString()}</p>
      </Card>
      <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white" data-name="displayed-tweets-card">
        <h3 className="text-lg font-semibold mb-2">표시 중인 트윗</h3>
        <p className="text-3xl font-bold">{tweetsLength}</p>
      </Card>
      <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white" data-name="platform-card">
        <h3 className="text-lg font-semibold mb-2">플랫폼</h3>
        <p className="text-3xl font-bold">Twitter/X</p>
      </Card>
    </Grid>
  );
}