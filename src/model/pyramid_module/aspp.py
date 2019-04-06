from torch import cat, nn


class DilationModule(nn.Module):

    def __init__(self, in_channels, out_channels, kernel_size, padding=0, dilation_rate=1):
        super().__init__()
        self.dil_conv = nn.Conv2d(in_channels, out_channels, kernel_size, padding=padding, dilation=dilation_rate)
        self.batch_norm = nn.BatchNorm2d(out_channels)

    def forward(self, input_tensor):
        input_tensor = self.dil_conv(input_tensor)
        return self.batch_norm(input_tensor)


class ASPPModule(nn.Module):

    def __init__(self, in_channels, out_channels=256, kernel_size=3, atrous_rates=(6, 12, 18), final_classes=21):
        super().__init__()
        # super(ASPP, self).__init__()
        dilation_dict = dict()
        for rate in atrous_rates:
            dilation_dict['rate_{}'.format(rate)] = DilationModule(in_channels, out_channels, kernel_size, padding=rate, dilation_rate=rate)

        self.dilations = nn.ModuleDict(dilation_dict)
        self.avg_conv = DilationModule(in_channels, out_channels, kernel_size=1)
        self.avg_conv2 = DilationModule(4*out_channels, out_channels, kernel_size=1)
        self.output_conv_logits = nn.Conv2d(out_channels, final_classes, kernel_size=1)

    def forward(self, input_tensor):
        final_tensor = None
        for rate_conv in self.dilations.keys():
            dil_rate_tensor = self.dilations[rate_conv](input_tensor)
            final_tensor = cat((final_tensor, dil_rate_tensor), dim=1)

        avg_pooling = nn.AvgPool2d(input_tensor.size()[-2:])(input_tensor)
        avg_pooling = self.avg_conv(avg_pooling)
        avg_pooling = nn.functional.interpolate(avg_pooling, input_tensor.size()[-2:], mode='bilinear')
        final_tensor = cat((final_tensor, avg_pooling), dim=1)
        final_tensor = self.avg_conv2(final_tensor)
        return self.output_conv_logits(final_tensor)